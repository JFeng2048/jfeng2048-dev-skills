# kotlinx.serialization：保留 @Serializable 类的序列化器
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keepclasseswithmembers class kotlinx.serialization.json.** { kotlinx.serialization.KSerializer serializer(...); }
-keep,includedescriptorclasses class {{package_name}}.**$$serializer { *; }
-keepclassmembers class {{package_name}}.** { *** Companion; }
-keepclasseswithmembers class {{package_name}}.** { kotlinx.serialization.KSerializer serializer(...); }

# Retrofit：保留接口方法上的泛型与注解
-keepattributes Signature, Exceptions
-keep,allowobfuscation interface retrofit2.http.*
-keep,allowobfuscation,allowshrinking interface {{package_name}}.data.remote.** { *; }
-keepclassmembers,allowshrinking,allowobfuscation class * {
    @retrofit2.http.* <methods>;
}

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**

# Room
-keep class * extends androidx.room.RoomDatabase
-dontwarn androidx.room.paging.**

# Hilt
-keep class dagger.hilt.** { *; }
-keep class javax.inject.** { *; }
