import SwiftUI

/// 登录页（表单范式）：输入校验 + 提交禁用 + 错误提示
///
/// 登录成功后不自己跳转：`SessionStore` 变化会让 `RootView` 切换整棵树。
struct LoginView: View {

    @StateObject private var viewModel: LoginViewModel

    init(repository: AuthRepository, session: SessionStore) {
        _viewModel = StateObject(wrappedValue: LoginViewModel(repository: repository, session: session))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.lg) {
                Text("login.title")
                    .font(.largeTitle.weight(.semibold))
                    .foregroundStyle(AppTheme.textPrimary)

                Text("login.subtitle")
                    .font(.subheadline)
                    .foregroundStyle(AppTheme.textSecondary)

                Spacer().frame(height: AppTheme.Spacing.md)

                TextField("login.username", text: $viewModel.username)
                    .textContentType(.username)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .inputStyle()

                SecureField("login.password", text: $viewModel.password)
                    .textContentType(.password)
                    .inputStyle()

                if let message = viewModel.errorMessage {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.red)
                }

                Button {
                    Task { await viewModel.submit() }
                } label: {
                    HStack(spacing: AppTheme.Spacing.sm) {
                        if viewModel.isLoading {
                            ProgressView()
                        }
                        Text("login.submit")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(!viewModel.canSubmit)

                Text("login.hint")
                    .font(.caption)
                    .foregroundStyle(AppTheme.textSecondary)
            }
            .padding(AppTheme.Spacing.xl)
        }
        .background(AppTheme.background)
        .scrollDismissesKeyboard(.interactively)
    }
}
