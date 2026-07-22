package ai.rytho.domain.model

data class FaceAnalysisResult(
    val age: Int,
    val gender: String,
    val emotion: String,
    val wuXingElement: String,
    val sanTingBalance: String,
    val summary: String
)
