package {{package_name}}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import {{package_name}}.core.designsystem.theme.AppTheme
import {{package_name}}.core.navigation.AppNavHost
import {{package_name}}.core.navigation.Routes
import {{package_name}}.feature.root.RootViewModel
import {{package_name}}.feature.root.SplashScreen
import dagger.hilt.android.AndroidEntryPoint

/**
 * 唯一 Activity。
 *
 * 这里只做三件事：开启边到边、挂主题、根据登录态决定起始页。
 * 业务逻辑一律在 ViewModel 与各 feature 中，不要往这里加。
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            AppTheme {
                val rootViewModel: RootViewModel = hiltViewModel()
                val state by rootViewModel.uiState.collectAsStateWithLifecycle()

                if (state.checked) {
                    // 已登录进首页，未登录进登录页；Navigation 只在确定后创建一次
                    AppNavHost(
                        startDestination = if (state.loggedIn) Routes.HOME else Routes.LOGIN,
                    )
                } else {
                    SplashScreen()
                }
            }
        }
    }
}
