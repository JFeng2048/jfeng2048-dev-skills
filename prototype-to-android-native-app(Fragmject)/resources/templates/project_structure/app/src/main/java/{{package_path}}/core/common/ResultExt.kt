package {{package_name}}.core.common

import kotlinx.coroutines.CancellationException

/**
 * 统一捕获异常并转成 Result。
 *
 * 注意：CancellationException 必须重新抛出，否则协程取消会被当成业务失败吞掉。
 */
suspend fun <T> safeResult(block: suspend () -> T): Result<T> = try {
    Result.success(block())
} catch (e: CancellationException) {
    throw e
} catch (e: Exception) {
    Result.failure(e)
}
