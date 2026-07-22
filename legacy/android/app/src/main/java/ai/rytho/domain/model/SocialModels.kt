package ai.rytho.domain.model

data class DirectMessage(
    val id: String = "",
    val senderId: String = "",
    val senderName: String = "",
    val receiverId: String = "",
    val text: String = "",
    val timestamp: Long = System.currentTimeMillis()
)

data class SocialPost(
    val id: String = "",
    val authorId: String = "",
    val authorName: String = "",
    val authorZodiac: String = "Scorpio ♏",
    val content: String = "",
    val timestamp: Long = System.currentTimeMillis(),
    val likesCount: Int = 0
)
