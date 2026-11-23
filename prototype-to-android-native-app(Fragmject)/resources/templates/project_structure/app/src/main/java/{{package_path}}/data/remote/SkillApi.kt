package {{package_name}}.data.remote

import {{package_name}}.data.remote.dto.ApiResponse
import {{package_name}}.data.remote.dto.SkillDto
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * 技能相关接口。
 *
 * 这里只声明路径与参数，不做任何数据加工；加工在 Repository。
 */
interface SkillApi {

    @GET("api/skills")
    suspend fun getSkills(
        @Query("page") page: Int,
        @Query("pageSize") pageSize: Int,
    ): ApiResponse<List<SkillDto>>

    @GET("api/skills/{id}")
    suspend fun getSkillDetail(@Path("id") id: String): ApiResponse<SkillDto>
}
