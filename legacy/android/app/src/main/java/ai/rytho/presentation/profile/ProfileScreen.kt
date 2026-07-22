package ai.rytho.presentation.profile

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
fun ProfileScreen(
    user: User?,
    onSignOut: () -> Unit,
    onNavigateToFaceAnalysis: () -> Unit = {},
    onNavigateToIChing: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {}
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Profil & Yıldız Haritam", color = Color(0xFFE7E0ED), fontWeight = FontWeight.Bold) },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Text("⚙️", fontSize = 20.sp)
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
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Profile Info Header Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF8B5CF6).copy(alpha = 0.3f), RoundedCornerShape(20.dp)),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
                shape = RoundedCornerShape(20.dp)
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Box(
                        modifier = Modifier
                            .size(72.dp)
                            .clip(CircleShape)
                            .background(
                                Brush.linearGradient(
                                    colors = listOf(Color(0xFF8B5CF6), Color(0xFFD4AF37))
                                )
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            user?.displayName?.take(1)?.uppercase() ?: "✦",
                            color = Color.White,
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        user?.displayName ?: user?.email ?: "Kozmik Gezgin",
                        style = MaterialTheme.typography.titleLarge,
                        color = Color(0xFFE7E0ED),
                        fontWeight = FontWeight.Bold
                    )

                    Text(
                        user?.email ?: "",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color(0xFF8B5CF6)
                    )
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Quick Access Features Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
                shape = RoundedCornerShape(20.dp)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Spiritüel Analiz Araçları", style = MaterialTheme.typography.titleMedium, color = Color(0xFFD4AF37), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))

                    Button(
                        onClick = onNavigateToFaceAnalysis,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF231F30)),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth().height(48.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("👤 Yüz Analizi (Mian Xiang & İlm-i Sima)", color = Color(0xFFE7E0ED))
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = onNavigateToIChing,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF231F30)),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth().height(48.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("☯ I Ching Kehanet Odası", color = Color(0xFFE7E0ED))
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // BaZi Four Pillars Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF15121B)),
                shape = RoundedCornerShape(20.dp)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("BaZi (Dört Sütun) Çin Astrolojisi", style = MaterialTheme.typography.titleMedium, color = Color(0xFF8B5CF6), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        BaZiPillar("Yıl", "Yang Ahşap", "Ejderha 🐉")
                        BaZiPillar("Ay", "Yin Ateş", "Yılan 🐍")
                        BaZiPillar("Gün", "Yang Toprak", "Kaplan 🐅")
                        BaZiPillar("Saat", "Yin Su", "Tavşan 🐇")
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            OutlinedButton(
                onClick = onSignOut,
                modifier = Modifier.fillMaxWidth().height(50.dp),
                shape = RoundedCornerShape(14.dp)
            ) {
                Text("Oturumu Kapat", color = Color(0xFFE5484D))
            }
        }
    }
}

@Composable
fun BaZiPillar(title: String, stem: String, branch: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(title, style = MaterialTheme.typography.labelSmall, color = Color(0xFF7A7090))
        Spacer(modifier = Modifier.height(4.dp))
        Text(stem, style = MaterialTheme.typography.bodySmall, color = Color(0xFFD4AF37), fontWeight = FontWeight.Bold)
        Text(branch, style = MaterialTheme.typography.bodySmall, color = Color(0xFFE7E0ED))
    }
}
