package ai.rytho.data.repository

import ai.rytho.data.remote.FaceAnalysisApi
import ai.rytho.domain.model.FaceAnalysisResult
import ai.rytho.domain.repository.FaceAnalysisRepository
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import javax.inject.Inject

class FaceAnalysisRepositoryImpl @Inject constructor(
    private val api: FaceAnalysisApi
) : FaceAnalysisRepository {
    override suspend fun analyzeFace(imageFile: File): Result<FaceAnalysisResult> {
        return try {
            val requestFile = imageFile.asRequestBody("image/*".toMediaTypeOrNull())
            val body = MultipartBody.Part.createFormData("file", imageFile.name, requestFile)
            
            val response = api.analyzeFace(body)
            if (response.status == "success" && response.data != null) {
                if (response.data.error != null) {
                    Result.failure(Exception(response.data.error))
                } else {
                    Result.success(
                        FaceAnalysisResult(
                            age = response.data.age,
                            gender = response.data.gender,
                            emotion = response.data.emotion,
                            wuXingElement = response.data.wu_xing_element,
                            sanTingBalance = response.data.san_ting_balance,
                            summary = response.data.face_reading_summary
                        )
                    )
                }
            } else {
                Result.failure(Exception("Unknown error from server"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
