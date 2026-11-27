package {{package_name}}.core.startup

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

interface StartupTask {
    val id: String
    val dependencies: Set<String>
    suspend fun run()
}

data class StartupTaskTiming(
    val taskId: String,
    val durationMillis: Long,
    val failure: Exception?,
    val skippedBecause: Set<String> = emptySet(),
)

fun interface StartupTaskObserver {
    fun onTaskFinished(timing: StartupTaskTiming)
}

class StartupTaskGraph(
    private val tasks: Collection<StartupTask>,
) {
    fun start(
        scope: CoroutineScope,
        observer: StartupTaskObserver = StartupTaskObserver {},
    ) {
        val ordered = topologicalOrder()
        scope.launch {
            val failedTaskIds = mutableSetOf<String>()
            for (task in ordered) {
                val blockedBy = task.dependencies.intersect(failedTaskIds)
                if (blockedBy.isNotEmpty()) {
                    failedTaskIds += task.id
                    observer.onTaskFinished(
                        StartupTaskTiming(
                            taskId = task.id,
                            durationMillis = 0,
                            failure = null,
                            skippedBecause = blockedBy,
                        ),
                    )
                    continue
                }

                val startedAt = System.nanoTime()
                var failure: Exception? = null
                try {
                    task.run()
                } catch (cancelled: CancellationException) {
                    observer.onTaskFinished(
                        StartupTaskTiming(
                            taskId = task.id,
                            durationMillis = (System.nanoTime() - startedAt) / 1_000_000,
                            failure = cancelled,
                        ),
                    )
                    throw cancelled
                } catch (error: Exception) {
                    failure = error
                }
                observer.onTaskFinished(
                    StartupTaskTiming(
                        taskId = task.id,
                        durationMillis = (System.nanoTime() - startedAt) / 1_000_000,
                        failure = failure,
                    ),
                )
                if (failure != null) failedTaskIds += task.id
            }
        }
    }

    private fun topologicalOrder(): List<StartupTask> {
        val byId = tasks.associateBy { it.id }
        require(byId.size == tasks.size) { "Startup task IDs must be unique" }
        tasks.forEach { task ->
            require(task.dependencies.all(byId::containsKey)) {
                "Unknown startup dependency for ${task.id}"
            }
        }

        val visited = mutableSetOf<String>()
        val visiting = mutableSetOf<String>()
        val result = mutableListOf<StartupTask>()

        fun visit(task: StartupTask) {
            require(task.id !in visiting) { "Startup task dependency cycle at ${task.id}" }
            if (!visited.add(task.id)) return
            visiting += task.id
            task.dependencies.forEach { visit(byId.getValue(it)) }
            visiting -= task.id
            result += task
        }

        tasks.forEach(::visit)
        return result
    }
}
