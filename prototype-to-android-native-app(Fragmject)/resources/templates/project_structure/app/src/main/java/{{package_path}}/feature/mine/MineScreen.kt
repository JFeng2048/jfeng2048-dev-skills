package {{package_name}}.feature.mine

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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import {{package_name}}.core.designsystem.component.AppTopBar
import {{package_name}}.core.designsystem.theme.Dimens

/**
 * 我的页面（个人中心 / 设置范式）：头部信息 + 设置行 + 退出登录。
 */
@Composable
fun MineScreen(
    onBack: () -> Unit,
    onLogout: () -> Unit,
    viewModel: MineViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.loggedOut) {
        if (state.loggedOut) onLogout()
    }

    MineContent(
        state = state,
        onBack = onBack,
        onLogoutClick = viewModel::logout,
    )
}

@Composable
private fun MineContent(
    state: MineUiState,
    onBack: () -> Unit,
    onLogoutClick: () -> Unit,
) {
    val context = LocalContext.current
    var showConfirm by remember { mutableStateOf(false) }

    if (showConfirm) {
        AlertDialog(
            onDismissRequest = { showConfirm = false },
            title = { Text(text = "退出登录") },
            text = { Text(text = "退出后需要重新登录，确定继续吗？") },
            confirmButton = {
                TextButton(
                    onClick = {
                        showConfirm = false
                        onLogoutClick()
                    },
                ) {
                    Text(text = "确定")
                }
            },
            dismissButton = {
                TextButton(onClick = { showConfirm = false }) {
                    Text(text = "取消")
                }
            },
        )
    }

    Scaffold(topBar = { AppTopBar(title = "我的", onBack = onBack) }) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
        ) {
            ProfileHeader(nickname = state.nickname)

            Spacer(modifier = Modifier.height(Dimens.sm))

            SettingRow(title = "我的发布") {
                Toast.makeText(context, "示例页面，待接入", Toast.LENGTH_SHORT).show()
            }
            HorizontalDivider(color = MaterialTheme.colorScheme.outline)
            SettingRow(title = "设置") {
                Toast.makeText(context, "示例页面，待接入", Toast.LENGTH_SHORT).show()
            }
            HorizontalDivider(color = MaterialTheme.colorScheme.outline)
            SettingRow(title = "关于") {
                Toast.makeText(context, "{{app_name}} v1.0.0", Toast.LENGTH_SHORT).show()
            }

            Spacer(modifier = Modifier.weight(1f))

            OutlinedButton(
                onClick = { showConfirm = true },
                enabled = !state.isLoading,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(Dimens.lg),
            ) {
                Text(text = "退出登录", color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun ProfileHeader(nickname: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(Dimens.lg),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(Dimens.avatarSize)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primaryContainer),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = nickname.take(1),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )
        }

        Spacer(modifier = Modifier.size(Dimens.md))

        Column(verticalArrangement = Arrangement.spacedBy(Dimens.xs)) {
            Text(
                text = nickname,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = "已登录（mock 账号）",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SettingRow(title: String, onClick: () -> Unit) {
    Surface(onClick = onClick, color = MaterialTheme.colorScheme.surface) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = Dimens.lg, vertical = Dimens.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(modifier = Modifier.weight(1f))
            Icon(
                imageVector = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
