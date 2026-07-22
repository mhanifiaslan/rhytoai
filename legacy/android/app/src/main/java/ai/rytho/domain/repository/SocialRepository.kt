package ai.rytho.domain.repository

import ai.rytho.domain.model.DirectMessage
import ai.rytho.domain.model.SocialPost
import kotlinx.coroutines.flow.Flow

interface SocialRepository {
    fun getSocialPosts(): Flow<List<SocialPost>>
    suspend fun createPost(content: String, authorName: String, zodiac: String): Result<Unit>
    fun getDirectMessages(currentUserId: String, peerUserId: String): Flow<List<DirectMessage>>
    suspend fun sendDirectMessage(message: DirectMessage): Result<Unit>
}
