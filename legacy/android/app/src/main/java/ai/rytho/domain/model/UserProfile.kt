package ai.rytho.domain.model

data class UserProfile(
    val uid: String = "",
    val displayName: String = "",
    val email: String = "",
    val photoUrl: String? = null,
    val birthDate: String = "", // YYYY-MM-DD
    val birthTime: String = "", // HH:mm
    val birthCity: String = "",
    val latitude: Double? = null,
    val longitude: Double? = null,
    val sunSign: String = "",
    val moonSign: String = "",
    val ascendantSign: String = "",
    val onboardingCompleted: Boolean = false
)
