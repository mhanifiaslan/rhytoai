package ai.rytho.domain.repository

import ai.rytho.domain.model.FaceAnalysisResult
import java.io.File

interface FaceAnalysisRepository {
    suspend fun analyzeFace(imageFile: File): Result<FaceAnalysisResult>
}
