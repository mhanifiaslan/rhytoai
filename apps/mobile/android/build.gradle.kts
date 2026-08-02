allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
// Eklentilerin Java ve Kotlin hedeflerini AYNI sürüme sabitler.
//
// `tflite_flutter` derlemeyi şu hatayla düşürüyordu:
//   Inconsistent JVM-target compatibility ... 'compileDebugJavaWithJavac' (11)
//   ve 'compileDebugKotlin' (21)
//
// Eklenti kendi Java hedefini 11'e sabitliyor, Kotlin eklentisi ise yeni
// araçlarda JDK'nin sürümünü (21) alıyor. Uygulama modülü zaten 17
// kullanıyor; aynı değeri bütün alt projelere veriyoruz ki her eklenti için
// tek tek uğraşmayalım.
//
// `configureEach` TEMBEL çalışır ve bu şart: `afterEvaluate` denendi ve
// "Cannot run Project.afterEvaluate when the project is already evaluated"
// hatası verdi — aşağıdaki `evaluationDependsOn` projeleri çoktan
// değerlendirmiş oluyor. Blok da onun ÜSTÜNDE durmalı.
// `afterEvaluate` şart: Android eklentisi kendi `compileOptions` değerini
// (11) proje değerlendirilirken yazıyor, bizim ayarımız ondan SONRA gelmeli.
// Blok da `evaluationDependsOn`'un ÜSTÜNDE durmalı — altında olunca Gradle
// "Cannot run Project.afterEvaluate when the project is already evaluated"
// diyor.
subprojects {
    afterEvaluate {
        // Android eklentisinin `compileOptions`'ı — asıl kaynak burası.
        // `withGroovyBuilder` kullanılıyor çünkü AGP tipleri kök derleme
        // betiğinin sınıf yolunda yok ve tip için bağımlılık eklemek
        // gereksiz.
        extensions.findByName("android")?.withGroovyBuilder {
            "compileOptions" {
                setProperty("sourceCompatibility", JavaVersion.VERSION_17)
                setProperty("targetCompatibility", JavaVersion.VERSION_17)
            }
        }
        tasks.withType<JavaCompile>().configureEach {
            sourceCompatibility = JavaVersion.VERSION_17.toString()
            targetCompatibility = JavaVersion.VERSION_17.toString()
            // `options.release` KULLANILAMAZ: AGP bunu açıkça reddediyor,
            // çünkü Android API'lerine karşı derlemek için gereken
            // bootclasspath'i kurmasını engelliyor (issuetracker 278800528).
        }
        tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>()
            .configureEach {
                compilerOptions.jvmTarget.set(
                    org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17,
                )
            }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
