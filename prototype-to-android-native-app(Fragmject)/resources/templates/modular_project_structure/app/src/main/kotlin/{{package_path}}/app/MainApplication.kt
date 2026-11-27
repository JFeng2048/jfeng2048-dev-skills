package {{package_name}}.app

import android.app.Application
import android.util.Log
import {{package_name}}.core.startup.StartupTaskGraph
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

@HiltAndroidApp
class MainApplication : Application() {
    private val startupScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        StartupTaskGraph(emptyList()).start(startupScope) { timing ->
            when {
                timing.skippedBecause.isNotEmpty() -> Log.w(
                    TAG,
                    "Startup task ${timing.taskId} skipped after ${timing.skippedBecause}",
                )
                timing.failure == null -> Log.d(
                    TAG,
                    "Startup task ${timing.taskId} finished in ${timing.durationMillis}ms",
                )
                else -> Log.e(
                    TAG,
                    "Startup task ${timing.taskId} failed after ${timing.durationMillis}ms " +
                        "(${timing.failure::class.simpleName})",
                )
            }
        }
    }

    private companion object {
        const val TAG = "MainApplication"
    }
}
