import Foundation

/// 登录请求体
struct LoginRequest: Encodable {
    let username: String
    let password: String
}

/// 登录响应体
struct LoginResponse: Decodable {
    let token: String?
    let nickname: String?
}
