package com.example.skillswap.feature.detail

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.example.skillswap.core.designsystem.component.AppTopBar
import com.example.skillswap.core.designsystem.component.ErrorView
import com.example.skillswap.core.designsystem.component.LoadingView
import com.example.skillswap.core.designsystem.theme.Dimens
import com.example.skillswap.data.model.Skill

/**
 * 详情页（详情范式）：顶部标题栏 + 可滚动内容 + 底部固定操作栏。
 */
@Composable
fun DetailScreen(
    onBack: () -> Unit,
    viewModel: DetailViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    DetailContent(
        state = state,
        onBack = onBack,
        onRetry = viewModel::retry,
    )
}

@Composable
private fun DetailContent(
    state: DetailUiState,
    onBack: () -> Unit,
    onRetry: () -> Unit,
) {
    val context = LocalContext.current
    val skill = state.skill

    Scaffold(
        topBar = { AppTopBar(title = "详情", onBack = onBack) },
        bottomBar = {
            if (skill != null) {
                Surface(color = MaterialTheme.colorScheme.surface, shadowElevation = 8.dp) {
                    Button(
                        onClick = {
                            Toast.makeText(context, "已发起联系请求（示例）", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(Dimens.lg),
                    ) {
                        Text(text = "联系 TA")
                    }
                }
            }
        },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
        ) {
            when {
                state.isLoading -> LoadingView()
                state.error != null && skill == null -> ErrorView(
                    message = state.error.orEmpty(),
                    onRetry = onRetry,
                )
                skill == null -> ErrorView(message = "内容不存在", onRetry = onRetry)
                else -> DetailBody(skill = skill)
            }
        }
    }
}

@Composable
private fun DetailBody(skill: Skill) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(Dimens.lg),
    ) {
        AsyncImage(
            model = skill.avatar,
            contentDescription = skill.title,
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp)
                .clip(RoundedCornerShape(Dimens.cardRadius))
                .background(MaterialTheme.colorScheme.surfaceVariant),
        )

        Spacer(modifier = Modifier.height(Dimens.lg))

        Text(
            text = skill.title,
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )

        Spacer(modifier = Modifier.height(Dimens.sm))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = skill.author,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = skill.priceText,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary,
            )
        }

        Spacer(modifier = Modifier.height(Dimens.md))
        HorizontalDivider(color = MaterialTheme.colorScheme.outline)
        Spacer(modifier = Modifier.height(Dimens.md))

        if (skill.tags.isNotEmpty()) {
            Text(
                text = skill.tags.joinToString(" / "),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(modifier = Modifier.height(Dimens.sm))
        }

        Text(
            text = skill.description.ifBlank { "暂无详细介绍" },
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )

        Spacer(modifier = Modifier.height(Dimens.xl))
    }
}
