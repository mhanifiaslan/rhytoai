package ai.rytho.di

import ai.rytho.data.repository.FaceAnalysisRepositoryImpl
import ai.rytho.domain.repository.FaceAnalysisRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindFaceAnalysisRepository(
        faceAnalysisRepositoryImpl: FaceAnalysisRepositoryImpl
    ): FaceAnalysisRepository

    @Binds
    @Singleton
    abstract fun bindChatRepository(
        chatRepositoryImpl: ai.rytho.data.repository.ChatRepositoryImpl
    ): ai.rytho.domain.repository.ChatRepository

    @Binds
    @Singleton
    abstract fun bindUserRepository(
        userRepositoryImpl: ai.rytho.data.repository.UserRepositoryImpl
    ): ai.rytho.domain.repository.UserRepository

    @Binds
    @Singleton
    abstract fun bindSocialRepository(
        socialRepositoryImpl: ai.rytho.data.repository.SocialRepositoryImpl
    ): ai.rytho.domain.repository.SocialRepository
}
