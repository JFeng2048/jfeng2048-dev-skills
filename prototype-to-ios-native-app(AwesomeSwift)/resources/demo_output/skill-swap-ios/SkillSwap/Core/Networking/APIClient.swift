import Foundation
import Alamofire

/// HTTP 客户端：唯一发起网络请求的地方
///
/// 统一负责：baseURL、超时、token 注入、`{code,message,data}` 解包、错误归一化。
final class APIClient {

    private let session: Session
    private let decoder: JSONDecoder

    init(tokenStorage: TokenStorage) {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 15
        configuration.timeoutIntervalForResource = 30

        self.session = Session(
            configuration: configuration,
            interceptor: AuthInterceptor(tokenStorage: tokenStorage)
        )
        self.decoder = JSONDecoder()
    }

    /// 发起请求并解包业务数据
    /// - Parameter target: 接口定义
    /// - Returns: 解包后的 `data` 字段
    func request<T: Decodable>(_ target: APITarget) async throws -> T {
        let response = await session
            .request(target)
            .validate()
            .serializingDecodable(APIResponse<T>.self, decoder: decoder)
            .response

        switch response.result {
        case .success(let envelope):
            guard envelope.code == 0 else {
                throw APIError.business(code: envelope.code, message: envelope.message)
            }
            guard let data = envelope.data else {
                throw APIError.emptyData
            }
            return data
        case .failure(let error):
            throw APIError.from(error)
        }
    }
}
