package {{package_name}}.feature.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import {{package_name}}.core.designsystem.theme.Dimens

/**
 * 登录页（表单范式）：输入校验 + 提交禁用 + 错误提示。
 * 登录成功后通过 onLoginSuccess 回调交给导航层，自己不做跳转。
 */
@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit,
    viewModel: LoginViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.loggedIn) {
        if (state.loggedIn) onLoginSuccess()
    }

    LoginContent(
        state = state,
        onUsernameChange = viewModel::onUsernameChange,
        onPasswordChange = viewModel::onPasswordChange,
        onSubmit = viewModel::submit,
    )
}

@Composable
private fun LoginContent(
    state: LoginUiState,
    onUsernameChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onSubmit: () -> Unit,
) {
    Scaffold { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Dimens.xl, vertical = Dimens.xxl),
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = "欢迎回来",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(modifier = Modifier.height(Dimens.xs))
            Text(
                text = "登录后即可查看完整内容",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(modifier = Modifier.height(Dimens.xxl))

            OutlinedTextField(
                value = state.username,
                onValueChange = onUsernameChange,
                label = { Text(text = "账号") },
                singleLine = true,
                enabled = !state.isLoading,
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(modifier = Modifier.height(Dimens.md))

            OutlinedTextField(
                value = state.password,
                onValueChange = onPasswordChange,
                label = { Text(text = "密码") },
                singleLine = true,
                enabled = !state.isLoading,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
            )

            if (state.error != null) {
                Spacer(modifier = Modifier.height(Dimens.sm))
                Text(
                    text = state.error.orEmpty(),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error,
                )
            }

            Spacer(modifier = Modifier.height(Dimens.xl))

            Button(
                onClick = onSubmit,
                enabled = state.canSubmit,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (state.isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary,
                    )
                } else {
                    Text(text = "登录")
                }
            }

            Spacer(modifier = Modifier.height(Dimens.md))

            Text(
                text = "提示：mock 模式下账号随意，密码不少于 6 位",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
