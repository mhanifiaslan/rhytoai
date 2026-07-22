package ai.rytho.data.remote

import retrofit2.http.GET
import retrofit2.http.Query

data class NatalChartRequest(
    val name: String,
    val year: Int,
    val month: Int,
    val day: Int,
    val hour: Int = 12,
    val minute: Int = 0,
    val city: String = "Istanbul",
    val nation: String = "TR"
)

data class NatalChartData(
    val sun_sign: String = "Scorpio",
    val moon_sign: String = "Pisces",
    val ascendant: String = "Cancer",
    val report: String = ""
)

data class NatalChartResponse(
    val status: String,
    val data: NatalChartData?
)

interface AstrologyApi {
    @GET("api/v1/astrology/natal-chart")
    suspend fun getNatalChart(
        @Query("name") name: String,
        @Query("year") year: Int,
        @Query("month") month: Int,
        @Query("day") day: Int,
        @Query("hour") hour: Int = 12,
        @Query("minute") minute: Int = 0,
        @Query("city") city: String = "Istanbul",
        @Query("nation") nation: String = "TR"
    ): NatalChartResponse
}
