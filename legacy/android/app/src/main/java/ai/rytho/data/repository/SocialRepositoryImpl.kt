package ai.rytho.data.repository

import ai.rytho.domain.model.DirectMessage
import ai.rytho.domain.model.SocialPost
import ai.rytho.domain.repository.SocialRepository
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.Query
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.tasks.await
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SocialRepositoryImpl @Inject constructor(
    private val firestore: FirebaseFirestore
) : SocialRepository {

    override fun getSocialPosts(): Flow<List<SocialPost>> = callbackFlow {
        val listener = firestore.collection("posts")
            .orderBy("timestamp", Query.Direction.DESCENDING)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    close(error)
                    return@addSnapshotListener
                }
                val posts = snapshot?.documents?.mapNotNull { doc ->
                    doc.toObject(SocialPost::class.java)?.copy(id = doc.id)
                } ?: emptyList()
                trySend(posts)
            }
        awaitClose { listener.remove() }
    }

    override suspend fun createPost(content: String, authorName: String, zodiac: String): Result<Unit> {
        return try {
            val docRef = firestore.collection("posts").document()
            val post = SocialPost(
                id = docRef.id,
                authorName = authorName,
                authorZodiac = zodiac,
                content = content,
                timestamp = System.currentTimeMillis()
            )
            docRef.set(post).await()
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override fun getDirectMessages(currentUserId: String, peerUserId: String): Flow<List<DirectMessage>> = callbackFlow {
        val chatId = getChatId(currentUserId, peerUserId)
        val listener = firestore.collection("chats")
            .document(chatId)
            .collection("messages")
            .orderBy("timestamp", Query.Direction.ASCENDING)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    close(error)
                    return@addSnapshotListener
                }
                val messages = snapshot?.documents?.mapNotNull { doc ->
                    doc.toObject(DirectMessage::class.java)?.copy(id = doc.id)
                } ?: emptyList()
                trySend(messages)
            }
        awaitClose { listener.remove() }
    }

    override suspend fun sendDirectMessage(message: DirectMessage): Result<Unit> {
        return try {
            val chatId = getChatId(message.senderId, message.receiverId)
            val docRef = firestore.collection("chats")
                .document(chatId)
                .collection("messages")
                .document()
            docRef.set(message.copy(id = docRef.id)).await()
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun getChatId(user1: String, user2: String): String {
        return if (user1 < user2) "${user1}_${user2}" else "${user2}_${user1}"
    }
}
