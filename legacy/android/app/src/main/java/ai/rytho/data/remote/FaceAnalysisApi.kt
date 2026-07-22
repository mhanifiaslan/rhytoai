package ai.rytho.data.remote

import okhttp3.MultipartBody
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface FaceAnalysisApi {
    @Multipart
    @POST("api/v1/face-reading/analyze")
    suspend fun analyzeFace(
        @Part file: MultipartBody.Part
    ): FaceAnalysisResponse
}

data class FaceAnalysisResponse(
    val status: String,
    val data: FaceAnalysisData?
)

data class FaceAnalysisData(
    val age: Int,
    val gender: String,
    val emotion: String,
    val wu_xing_element: String,
    val san_ting_balance: String,
    val face_reading_summary: String,
    val error: String? = null
)
