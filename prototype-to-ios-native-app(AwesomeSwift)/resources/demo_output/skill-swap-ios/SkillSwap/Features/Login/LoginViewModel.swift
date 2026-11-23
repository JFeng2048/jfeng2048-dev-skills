import Foundation
import Combine

/// 登录页 ViewModel：校验 + 调 Repository + 写入会话
@MainActor
final class LoginViewModel: ObservableObject {

    @Published var username = ""
    @Published var password = ""
    @Published private(set) var isLoading = false
    @Published private(set) var errorMessage: String?

    private let repository: AuthRepository
    private let session: SessionStore

    init(repository: AuthRepository, session: SessionStore) {
        self.repository = repository
        self.session = session
    }

    /// 提交按钮可用条件
    var canSubmit: Bool {
        !username.trimmingCharacters(in: .whitespaces).isEmpty
            && password.count >= 6
            && !isLoading
    }

    func submit() async {
        let name = username.trimmingCharacters(in: .whitespaces)
        guard !name.isEmpty, password.count >= 6 else {
            errorMessage = String(localized: "login.error.invalid")
            return
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let token = try await repository.login(username: name, password: password)
            session.signIn(token: token)
        } catch {
            errorMessage = APIError.from(error).localizedDescription
        }
    }
}
