import Foundation
import Alamofire

/// 请求拦截器：自动带上 `Authorization: Bearer <token>`
///
/// 刷新 token 的逻辑放在 `refresh` 里（模板留空，按需实现）。
final class AuthInterceptor: RequestInterceptor {

    private let tokenStorage: TokenStorage

    init(tokenStorage: TokenStorage) {
        self.tokenStorage = tokenStorage
    }

    func adapt(
        _ urlRequest: URLRequest,
        for session: Session,
        completion: @escaping (Result<URLRequest, Error>) -> Void
    ) {
        var request = urlRequest
        if let token = tokenStorage.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        completion(.success(request))
    }
}
