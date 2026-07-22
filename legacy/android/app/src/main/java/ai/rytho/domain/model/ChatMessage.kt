package ai.rytho.domain.model

enum class MessageSender {
    USER,
    CONFIDANT
}

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val sender: MessageSender,
    val text: String,
    val timestamp: Long = System.currentTimeMillis()
)
