package ai.rytho.di

import ai.rytho.data.remote.FaceAnalysisApi
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    // PC Wi-Fi IP address for physical Android phone testing
    private const val BASE_URL = "http://192.168.1.95:8000/"

    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit {
        val okHttpClient = okhttp3.OkHttpClient.Builder()
            .connectTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .writeTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideFaceAnalysisApi(retrofit: Retrofit): FaceAnalysisApi {
        return retrofit.create(FaceAnalysisApi::class.java)
    }

    @Provides
    @Singleton
    fun provideChatApi(retrofit: Retrofit): ai.rytho.data.remote.ChatApi {
        return retrofit.create(ai.rytho.data.remote.ChatApi::class.java)
    }

    @Provides
    @Singleton
    fun provideAstrologyApi(retrofit: Retrofit): ai.rytho.data.remote.AstrologyApi {
        return retrofit.create(ai.rytho.data.remote.AstrologyApi::class.java)
    }

    @Provides
    @Singleton
    fun provideIChingApi(retrofit: Retrofit): ai.rytho.data.remote.IChingApi {
        return retrofit.create(ai.rytho.data.remote.IChingApi::class.java)
    }
}
