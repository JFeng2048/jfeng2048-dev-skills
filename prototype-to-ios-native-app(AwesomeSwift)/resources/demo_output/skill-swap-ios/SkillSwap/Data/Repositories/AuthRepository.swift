import Foundation

/// 认证数据接缝
@MainActor
protocol AuthRepository {
    /// 成功返回 token
    func login(username: String, password: String) async throws -> String
}

@MainActor
final class DefaultAuthRepository: AuthRepository {

    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func login(username: String, password: String) async throws -> String {
        if AppConfig.useMock {
            try await Task.sleep(nanoseconds: 400_000_000)
            guard let token = MockData.login(username: username, password: password) else {
                throw APIError.business(
                    code: 400,
                    message: String(localized: "login.error.invalid")
                )
            }
            return token
        }

        let response: LoginResponse = try await client.request(
            .login(username: username, password: password)
        )
        guard let token = response.token, !token.isEmpty else {
            throw APIError.business(code: 401, message: String(localized: "login.error.failed"))
        }
        return token
    }
}
