package {{package_name}}

import {{package_name}}.data.mock.MockData
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * 纯 Kotlin 单测，不依赖 Android 框架，可直接 ./gradlew test 运行。
 */
class MockDataTest {

    @Test
    fun `首页分页按每页十条切片`() {
        val page0 = MockData.pageSkills(page = 0, pageSize = 10)
        val page1 = MockData.pageSkills(page = 1, pageSize = 10)

        assertEquals(10, page0.size)
        assertEquals(2, page1.size)
        // 两页数据不重复
        assertEquals(12, (page0 + page1).map { it.id }.distinct().size)
    }

    @Test
    fun `详情按 id 能命中`() {
        assertNotNull(MockData.skillById("1"))
        assertNull(MockData.skillById("not-exist"))
    }

    @Test
    fun `mock 登录密码太短应失败`() {
        assertNull(MockData.login(username = "u", password = "123"))
        assertNotNull(MockData.login(username = "u", password = "123456"))
    }
}
