import Foundation

/// 统一响应体：`{ "code": 0, "message": "ok", "data": ... }`
///
/// 字段缺失时给默认值，避免后端小改动直接导致解码失败。
struct APIResponse<Data: Decodable>: Decodable {

    let code: Int
    let message: String
    let data: Data?

    private enum CodingKeys: String, CodingKey {
        case code
        case message
        case data
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        code = try container.decodeIfPresent(Int.self, forKey: .code) ?? 0
        message = try container.decodeIfPresent(String.self, forKey: .message) ?? ""
        data = try container.decodeIfPresent(Data.self, forKey: .data)
    }
}
