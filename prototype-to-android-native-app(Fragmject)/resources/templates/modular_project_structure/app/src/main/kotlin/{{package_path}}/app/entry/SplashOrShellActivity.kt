package {{package_name}}.app.entry

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import {{package_name}}.core.designsystem.theme.AppTheme
import {{package_name}}.core.router.FeatureEntry
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class SplashOrShellActivity : ComponentActivity() {
    @Inject
    lateinit var featureEntries: Set<@JvmSuppressWildcards FeatureEntry>

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AppTheme {
                AppNavHost(entries = featureEntries)
            }
        }
    }
}

@Composable
private fun AppNavHost(
    entries: Set<FeatureEntry>,
    modifier: Modifier = Modifier,
) {
    val navController = rememberNavController()
    val orderedEntries = entries.sortedBy { it.startDestination }
    val startDestination = orderedEntries.firstOrNull { it.isDefaultStartDestination }
        ?.startDestination
        ?: orderedEntries.firstOrNull()?.startDestination
        ?: "app/empty"

    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier,
    ) {
        orderedEntries.forEach { entry ->
            entry.registerGraph(this, navController)
        }
        if (orderedEntries.isEmpty()) {
            composable("app/empty") { }
        }
    }
}
