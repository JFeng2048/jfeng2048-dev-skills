package {{package_name}}.core.startup

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StartupTaskGraphTest {
    @Test
    fun runsTasksInDependencyOrderAndReportsTiming() = runBlocking {
        val completed = mutableListOf<String>()
        val timings = mutableListOf<StartupTaskTiming>()
        val tasks = listOf(
            task("second", setOf("first"), completed),
            task("first", emptySet(), completed),
        )

        StartupTaskGraph(tasks)
            .start(this, StartupTaskObserver(timings::add))
            .join()

        assertEquals(listOf("first", "second"), completed)
        assertEquals(listOf("first", "second"), timings.map { it.taskId })
        assertTrue(timings.all { it.durationMillis >= 0 && it.failure == null })
    }

    @Test
    fun rejectsDependencyCyclesBeforeLaunching() {
        val tasks = listOf(
            task("first", setOf("second"), mutableListOf()),
            task("second", setOf("first"), mutableListOf()),
        )
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Unconfined)

        try {
            StartupTaskGraph(tasks).start(scope)
            throw AssertionError("Expected a dependency cycle to be rejected")
        } catch (_: IllegalArgumentException) {
            // Expected: invalid graphs fail before startup work is scheduled.
        } finally {
            scope.coroutineContext[Job]?.cancel()
        }
    }

    @Test
    fun reportsFailureAndSkipsOnlyDependentTasks() = runBlocking {
        val completed = mutableListOf<String>()
        val timings = mutableListOf<StartupTaskTiming>()
        val tasks = listOf(
            task("failed", emptySet(), completed, IllegalStateException("fixture")),
            task("dependent", setOf("failed"), completed),
            task("independent", emptySet(), completed),
        )

        StartupTaskGraph(tasks)
            .start(this, StartupTaskObserver(timings::add))
            .join()

        assertEquals(listOf("failed", "independent"), completed)
        assertNotNull(timings.first { it.taskId == "failed" }.failure)
        assertEquals(setOf("failed"), timings.first { it.taskId == "dependent" }.skippedBecause)
        assertTrue(timings.first { it.taskId == "independent" }.failure == null)
    }

    private fun task(
        taskId: String,
        taskDependencies: Set<String>,
        completed: MutableList<String>,
        failure: Exception? = null,
    ) = object : StartupTask {
        override val id = taskId
        override val dependencies = taskDependencies

        override suspend fun run() {
            completed += id
            failure?.let { throw it }
        }
    }
}
