package {{package_name}}.core.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import {{package_name}}.feature.detail.DetailScreen
import {{package_name}}.feature.home.HomeScreen
import {{package_name}}.feature.login.LoginScreen
import {{package_name}}.feature.mine.MineScreen

/**
 * 全局导航图（唯一 NavHost）。
 *
 * 新增页面步骤：
 * 1. 在 Routes 里加常量；
 * 2. 在这里加 composable(...)；
 * 3. 页面内部通过回调把跳转意图抛给上层，不要自己拿 NavController。
 */
@Composable
fun AppNavHost(
    startDestination: String,
    modifier: Modifier = Modifier,
) {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier,
    ) {
        // 登录页：不要求登录态
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Routes.HOME) {
                        popUpTo(Routes.LOGIN) { inclusive = true }
                    }
                },
            )
        }

        // 首页列表
        composable(Routes.HOME) {
            HomeScreen(
                onSkillClick = { skillId -> navController.navigate(Routes.detail(skillId)) },
                onOpenMine = { navController.navigate(Routes.MINE) },
            )
        }

        // 我的（设置入口）
        composable(Routes.MINE) {
            MineScreen(
                onBack = { navController.popBackStack() },
                onLogout = {
                    navController.navigate(Routes.LOGIN) {
                        // 清空返回栈，避免退出后按返回键又回到内页
                        popUpTo(navController.graph.id) { inclusive = true }
                    }
                },
            )
        }

        // 详情页：从 path 参数取 id，ViewModel 用 SavedStateHandle 读取
        composable(
            route = Routes.DETAIL,
            arguments = listOf(navArgument(Routes.ARG_SKILL_ID) { type = NavType.StringType }),
        ) {
            DetailScreen(onBack = { navController.popBackStack() })
        }
    }
}
