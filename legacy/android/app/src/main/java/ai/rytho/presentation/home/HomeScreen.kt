package ai.rytho.presentation.home

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ai.rytho.domain.model.User

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    user: User?,
    onNavigateToChat: () -> Unit,
    onNavigateToFaceAnalysis: () -> Unit,
    onNavigateToIChing: () -> Unit,
    onNavigateToAstrology: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Hoş geldin, ${user?.displayName?.ifEmpty { "Kozmik Gezgin" } ?: "Kozmik Gezgin"} ✦",
                            style = MaterialTheme.typography.titleMedium,
                            color = Color(0xFFE7E0ED),
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Bugünün Kozmik Hizalanması: %88 Yüksek",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFF8B5CF6)
                        )
                    }
                },
                actions = {
                    Box(
                        modifier = Modifier
                            .padding(end = 16.dp)
                            .size(36.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF231F30)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("✨", fontSize = 18.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0F0C1B))
            )
        },
        containerColor = Color(0xFF0F0C1B)
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Daily Cosmic Horoscope Hero Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(
                        width = 1.dp,
                        brush = Brush.linearGradient(listOf(Color(0xFF8B5CF6), Color(0xFFD4AF37))),
                        shape = RoundedCornerShape(20.dp)
                    ),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
                shape = RoundedCornerShape(20.dp)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("✦ GÜNÜN KOZMİK KEHANETİ ✦", style = MaterialTheme.typography.labelSmall, color = Color(0xFFD4AF37), letterSpacing = 2.sp)
                        Text("Akrep ♏ / Ay Balık ♓", style = MaterialTheme.typography.labelSmall, color = Color(0xFF8B5CF6))
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Bugün sezgisel enerjin doruk noktasında. İç sesini dinlemek ve yüz hatlarındaki mizaç dengeni fark etmek sana saklı kapıları açacak.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color(0xFFE7E0ED),
                        lineHeight = 22.sp
                    )
                }
            }

            Text("Spiritüel Rezonans Modülleri", style = MaterialTheme.typography.titleMedium, color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)

            // 2x2 Grid Module Cards
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    HomeModuleCard(
                        title = "Cosmic Confidant",
                        subtitle = "AI Spiritüel Sohbet",
                        icon = "✦",
                        accentColor = Color(0xFF8B5CF6),
                        modifier = Modifier.weight(1f),
                        onClick = onNavigateToChat
                    )
                    HomeModuleCard(
                        title = "Yüz Analizi",
                        subtitle = "Mian Xiang & İlm-i Sima",
                        icon = "👤",
                        accentColor = Color(0xFFD4AF37),
                        modifier = Modifier.weight(1f),
                        onClick = onNavigateToFaceAnalysis
                    )
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    HomeModuleCard(
                        title = "I Ching Odası",
                        subtitle = "Kadim Para Kehaneti",
                        icon = "☯",
                        accentColor = Color(0xFFE5484D),
                        modifier = Modifier.weight(1f),
                        onClick = onNavigateToIChing
                    )
                    HomeModuleCard(
                        title = "Kozmik Harita",
                        subtitle = "Natal & Gezegenler",
                        icon = "🔮",
                        accentColor = Color(0xFF30A46C),
                        modifier = Modifier.weight(1f),
                        onClick = onNavigateToAstrology
                    )
                }
            }

            // Element Balance Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
                shape = RoundedCornerShape(20.dp)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Günün Element & Mizaç Dengesi (Wu Xing)", style = MaterialTheme.typography.titleSmall, color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(12.dp))
                    ElementProgressBar("Toprak (Ahlat-ı Erbaa Sevda)", 0.40f, Color(0xFFD4AF37))
                    Spacer(modifier = Modifier.height(8.dp))
                    ElementProgressBar("Su (Ahlat-ı Erbaa Balgam)", 0.30f, Color(0xFF4285F4))
                    Spacer(modifier = Modifier.height(8.dp))
                    ElementProgressBar("Ateş (Ahlat-ı Erbaa Safra)", 0.20f, Color(0xFFE5484D))
                }
            }
        }
    }
}

@Composable
fun HomeModuleCard(
    title: String,
    subtitle: String,
    icon: String,
    accentColor: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        modifier = modifier
            .height(130.dp)
            .clickable { onClick() }
            .border(1.dp, accentColor.copy(alpha = 0.3f), RoundedCornerShape(16.dp)),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(icon, fontSize = 24.sp)
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(accentColor)
                )
            }
            Column {
                Text(title, style = MaterialTheme.typography.titleSmall, color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold)
                Text(subtitle, style = MaterialTheme.typography.labelSmall, color = Color(0xFF7A7090))
            }
        }
    }
}

@Composable
fun ElementProgressBar(label: String, progress: Float, color: Color) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(label, style = MaterialTheme.typography.labelSmall, color = Color(0xFF9B8FAE))
            Text("%${(progress * 100).toInt()}", style = MaterialTheme.typography.labelSmall, color = color, fontWeight = FontWeight.Bold)
        }
        Spacer(modifier = Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { progress },
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp)),
            color = color,
            trackColor = Color(0xFF231F30)
        )
    }
}
