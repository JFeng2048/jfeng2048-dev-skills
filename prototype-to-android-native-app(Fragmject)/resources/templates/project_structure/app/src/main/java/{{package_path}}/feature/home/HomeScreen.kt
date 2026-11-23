package {{package_name}}.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import {{package_name}}.core.designsystem.component.AppTopBar
import {{package_name}}.core.designsystem.component.EmptyView
import {{package_name}}.core.designsystem.component.ErrorView
import {{package_name}}.core.designsystem.component.ListEndView
import {{package_name}}.core.designsystem.component.LoadingRow
import {{package_name}}.core.designsystem.component.LoadingView
import {{package_name}}.core.designsystem.theme.Dimens
import {{package_name}}.feature.home.components.SkillCard

/**
 * 首页（列表范式）。
 *
 * 只做两件事：订阅 UiState 渲染、把用户操作转成 Event。
 */
@Composable
fun HomeScreen(
    onSkillClick: (String) -> Unit,
    onOpenMine: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    HomeContent(
        state = state,
        onRefresh = { viewModel.onEvent(HomeEvent.Refresh) },
        onLoadMore = { viewModel.onEvent(HomeEvent.LoadMore) },
        onRetry = { viewModel.onEvent(HomeEvent.Retry) },
        onSkillClick = onSkillClick,
        onOpenMine = onOpenMine,
    )
}

@Composable
private fun HomeContent(
    state: HomeUiState,
    onRefresh: () -> Unit,
    onLoadMore: () -> Unit,
    onRetry: () -> Unit,
    onSkillClick: (String) -> Unit,
    onOpenMine: () -> Unit,
) {
    Scaffold(
        topBar = {
            AppTopBar(
                title = "技能广场",
                actions = {
                    IconButton(onClick = onRefresh) {
                        Icon(imageVector = Icons.Default.Refresh, contentDescription = "刷新")
                    }
                    IconButton(onClick = onOpenMine) {
                        Icon(imageVector = Icons.Default.Person, contentDescription = "我的")
                    }
                },
            )
        },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
        ) {
            when {
                state.isLoading -> LoadingView()
                state.error != null && state.skills.isEmpty() -> ErrorView(
                    message = state.error.orEmpty(),
                    onRetry = onRetry,
                )
                state.skills.isEmpty() -> EmptyView(text = "暂无数据，去发布第一个技能吧")
                else -> SkillList(
                    state = state,
                    onSkillClick = onSkillClick,
                    onLoadMore = onLoadMore,
                )
            }
        }
    }
}

@Composable
private fun SkillList(
    state: HomeUiState,
    onSkillClick: (String) -> Unit,
    onLoadMore: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(Dimens.lg),
        verticalArrangement = Arrangement.spacedBy(Dimens.md),
    ) {
        items(items = state.skills, key = { it.id }) { skill ->
            SkillCard(skill = skill, onClick = { onSkillClick(skill.id) })
        }

        // 列表尾部：加载更多 / 触底自动加载 / 到底提示
        item(key = "footer") {
            when {
                state.isLoadingMore -> LoadingRow()
                state.hasMore -> LaunchedEffect(state.skills.size) { onLoadMore() }
                else -> ListEndView()
            }
        }
    }
}
