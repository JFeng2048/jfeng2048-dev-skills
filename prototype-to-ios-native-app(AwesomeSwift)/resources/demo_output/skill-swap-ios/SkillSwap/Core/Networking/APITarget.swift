import Foundation
import Alamofire

/// 接口清单：所有路径与参数集中在这里，页面不拼 URL。
///
/// 新增接口时加 case，并在 `path` / `method` / `parameters` 三处补分支。
enum APITarget {
    case skills(page: Int, pageSize: Int, keyword: String?)
    case skillDetail(id: String)
    case login(username: String, password: String)
}

extension APITarget: URLRequestConvertible {

    var path: String {
        switch self {
        case .skills:
            return "api/skills"
        case .skillDetail(let id):
            return "api/skills/\(id)"
        case .login:
            return "api/auth/login"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .login:
            return .post
        default:
            return .get
        }
    }

    var parameters: Parameters? {
        switch self {
        case .skills(let page, let pageSize, let keyword):
            var params: Parameters = ["page": page, "pageSize": pageSize]
            if let keyword, !keyword.isEmpty {
                params["keyword"] = keyword
            }
            return params
        case .skillDetail:
            return nil
        case .login(let username, let password):
            return ["username": username, "password": password]
        }
    }

    func asURLRequest() throws -> URLRequest {
        // 注意：baseURL 末尾必须带 /，path 不能以 / 开头
        let url = AppConfig.apiBaseURL.appendingPathComponent(path)
        var request = try URLRequest(url: url, method: method)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoding: ParameterEncoding = method == .get ? URLEncoding.default : JSONEncoding.default
        return try encoding.encode(request, with: parameters)
    }
}
