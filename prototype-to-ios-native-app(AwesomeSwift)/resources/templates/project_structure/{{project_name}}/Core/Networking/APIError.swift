import Foundation
import Alamofire

/// 统一错误类型：所有网络错误收敛到这里，再交给 ViewModel 展示
enum APIError: LocalizedError {
    /// 业务错误（后端 code != 0）
    case business(code: Int, message: String)
    /// 响应体 data 为空
    case emptyData
    /// 解码失败
    case decoding(Error)
    /// 传输层错误（超时 / 断网 / 非 2xx）
    case transport(Error)

    var errorDescription: String? {
        switch self {
        case .business(_, let message):
            return message.isEmpty ? "接口返回异常" : message
        case .emptyData:
            return "数据为空"
        case .decoding:
            return "数据解析失败，请稍后重试"
        case .transport(let error):
            return error.localizedDescription
        }
    }

    /// 把任意 Error 归类成 APIError
    static func from(_ error: Error) -> APIError {
        if let apiError = error as? APIError { return apiError }
        if error is DecodingError { return .decoding(error) }
        return .transport(error)
    }
}
