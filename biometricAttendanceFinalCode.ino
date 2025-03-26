#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Fingerprint.h>
#include <time.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define FINGERPRINT_SENSOR_RX 16  // Connect to sensor TX
#define FINGERPRINT_SENSOR_TX 17  // Connect to sensor RX

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&Serial2);

const char* ssid = "A";
const char* password = "00000000";
const char* server = "http://192.168.124.104:8000/";
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 19800;  // UTC+5:30 (India) = 5.5 * 3600 = 19800 seconds
const int daylightOffset_sec = 0;

int currentStudentId = -1;
bool isEnrolling = false;
unsigned long lastCheckTime = 0;
const unsigned long CHECK_INTERVAL = 1000; // Check every second
unsigned long lastDisplayUpdate = 0;
const unsigned long DISPLAY_UPDATE_INTERVAL = 1000; // Update display every second
bool timeSyncSuccess = false;
unsigned long lastTimeSyncAttempt = 0;
const unsigned long TIME_SYNC_INTERVAL = 300000; // Try to sync time every 5 minutes
unsigned long lastSpecialDayCheck = 0;
const unsigned long SPECIAL_DAY_CHECK_INTERVAL = 300000; // Check every 5 minutes

void deleteAllFingerprints() {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Deleting all");
    display.println("fingerprints...");
    display.display();

    uint8_t p = finger.emptyDatabase();
    if (p == FINGERPRINT_OK) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Database cleared!");
        display.println("All fingerprints");
        display.println("deleted.");
        display.display();
        Serial.println("Successfully cleared fingerprint database!");
        delay(2000);
    } else {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error clearing");
        display.println("database!");
        display.display();
        Serial.println("Error clearing fingerprint database!");
        delay(2000);
    }
}

void deleteFingerprint(int fingerprintID) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Deleting");
    display.println("fingerprint...");
    display.display();

    uint8_t p = finger.deleteModel(fingerprintID);
    if (p == FINGERPRINT_OK) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Fingerprint");
        display.println("deleted!");
        display.display();
        Serial.println("Successfully deleted fingerprint ID: " + String(fingerprintID));
        delay(2000);
    } else {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error deleting");
        display.println("fingerprint!");
        display.display();
        Serial.println("Error deleting fingerprint ID: " + String(fingerprintID));
        delay(2000);
    }
}

void setup() {
    Serial.begin(115200);
    Serial2.begin(57600, SERIAL_8N1, FINGERPRINT_SENSOR_RX, FINGERPRINT_SENSOR_TX);
    
    WiFi.begin(ssid, password);

    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("SSD1306 allocation failed");
        while (1);
    }
    
    // Initialize fingerprint sensor
    finger.begin(57600);
    
    // Check if fingerprint sensor is connected
    if (finger.verifyPassword()) {
        Serial.println("Found fingerprint sensor!");
        // Clear the fingerprint database on startup (ONLY UNCOMMENT THIS WHEN YOU WANT TO CLEAR ALL FINGERPRINTS)
        //deleteAllFingerprints();
    } else {
        Serial.println("Did not find fingerprint sensor :(");
        while (1);
    }

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 0);
    display.print("Connecting...");
    display.display();

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
    }

    // Initialize NTP
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    syncTime(); // Initial time sync attempt
}

void syncTime() {
    struct tm timeinfo;
    if(!getLocalTime(&timeinfo)){
        Serial.println("Failed to obtain time");
        timeSyncSuccess = false;
        return;
    }
    timeSyncSuccess = true;
    Serial.println("Time synchronized successfully");
}

void loop() {
    // Check for special working day periodically
    unsigned long currentMillis = millis();
    if (currentMillis - lastSpecialDayCheck >= SPECIAL_DAY_CHECK_INTERVAL) {
        int followDay;
        checkSpecialWorkingDay(followDay);
        lastSpecialDayCheck = currentMillis;
    }
    
    unsigned long currentTime = millis();
    
    if (currentTime - lastCheckTime >= CHECK_INTERVAL) {
        checkForEnrollmentCommand();
        checkForDeleteCommand();
        lastCheckTime = currentTime;
    }

    if (isEnrolling) {
        handleFingerprintEnrollment();
    } else {
        // Check for fingerprint for attendance
        uint8_t p = finger.getImage();
        if (p == FINGERPRINT_OK) {
            Serial.println("Finger detected, processing...");
            p = finger.image2Tz();
            if (p == FINGERPRINT_OK) {
                Serial.println("Image converted, searching...");
                p = finger.fingerFastSearch();
                if (p == FINGERPRINT_OK) {
                    // Check confidence score with lower threshold for demo
                    if (finger.confidence >= 30) {  // Lowered threshold to 30% for easier matching
                        Serial.println("Fingerprint matched! ID: " + String(finger.fingerID));
                        Serial.println("Confidence: " + String(finger.confidence));
                        // Fingerprint found, send attendance punch
                        sendAttendancePunch(finger.fingerID);
                    } else {
                        Serial.println("Match found but confidence too low: " + String(finger.confidence));
                        display.clearDisplay();
                        display.setCursor(0, 0);
                        display.println("Low confidence");
                        display.println("match!");
                        display.println("Try again");
                        display.display();
                        delay(2000);
                    }
                } else {
                    Serial.println("No match found");
                    display.clearDisplay();
                    display.setCursor(0, 0);
                    display.println("No match found!");
                    display.println("Try again");
                    display.display();
                    delay(2000);
                }
            } else {
                Serial.println("Error converting image");
                display.clearDisplay();
                display.setCursor(0, 0);
                display.println("Error reading");
                display.println("fingerprint!");
                display.println("Try again");
                display.display();
                delay(2000);
            }
        } else if (p == FINGERPRINT_NOFINGER) {
            // No finger detected, this is normal
        } else {
            Serial.println("Error getting image");
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println("Error reading");
            display.println("fingerprint!");
            display.println("Try again");
            display.display();
            delay(2000);
        }
        
        // Update display with current time/date
        if (currentTime - lastDisplayUpdate >= DISPLAY_UPDATE_INTERVAL) {
            displayCurrentTime();
            lastDisplayUpdate = currentTime;
        }
    }
}

void displayCurrentTime() {
    if (!timeSyncSuccess) {
        // Display fallback message when time sync fails
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Time Sync Failed");
        display.println("----------------");
        display.println("Ready for punch");
        display.display();
        
        // Try to sync time again
        if (millis() - lastTimeSyncAttempt >= TIME_SYNC_INTERVAL) {
            syncTime();
            lastTimeSyncAttempt = millis();
        }
        return;
    }

    struct tm timeinfo;
    if(!getLocalTime(&timeinfo)){
        Serial.println("Failed to obtain time");
        timeSyncSuccess = false;
        return;
    }

    display.clearDisplay();
    display.setCursor(0, 0);
    
    // Display date
    char dateStr[20];
    strftime(dateStr, sizeof(dateStr), "%Y-%m-%d", &timeinfo);
    display.println(dateStr);
    
    // Display time
    char timeStr[20];
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
    display.println(timeStr);
    
    // Display status
    display.println("----------------");
    display.println("Place your finger");
    display.println("to mark attendance");
    display.display();
}

void checkForEnrollmentCommand() {
    HTTPClient http;
    http.begin(String(server) + "api/check_enrollment_command/");
    int httpCode = http.GET();

    if (httpCode == 200) {
        String payload = http.getString();
        StaticJsonDocument<200> doc;
        deserializeJson(doc, payload);
        
        if (doc.containsKey("student_id") && doc["student_id"] != -1) {
            Serial.println("Received enrollment command for student ID: " + String(doc["student_id"].as<int>()));
            startEnrollment(doc["student_id"].as<int>());
        }
    }
    http.end();
}

void checkForDeleteCommand() {
    HTTPClient http;
    http.begin(String(server) + "api/check_delete_command/");
    int httpCode = http.GET();

    if (httpCode == 200) {
        String payload = http.getString();
        StaticJsonDocument<200> doc;
        deserializeJson(doc, payload);
        
        if (doc.containsKey("fingerprint_id") && doc["fingerprint_id"] != -1) {
            int fingerprintID = doc["fingerprint_id"].as<int>();
            const char* studentName = doc["name"].as<const char*>();
            const char* studentRoll = doc["roll"].as<const char*>();
            
            // Display student information before deletion
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println("Deleting Student:");
            display.println(studentName);
            display.println(studentRoll);
            display.println("----------------");
            display.println("Deleting");
            display.println("fingerprint...");
            display.display();
            delay(2000);
            
            Serial.println("Received delete command for fingerprint ID: " + String(fingerprintID));
            deleteFingerprint(fingerprintID);
        }
    }
    http.end();
}

void displayStudentList() {
    HTTPClient http;
    http.begin(String(server) + "api/students/"); 
    int httpCode = http.GET();

    if (httpCode == 200) {
        String payload = http.getString();
        StaticJsonDocument<1024> doc;
        deserializeJson(doc, payload);

        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Students:");
        
        for (JsonVariant student : doc.as<JsonArray>()) {
            display.println(student["name"].as<const char*>());
            if (!student["fingerprint_id"].isNull()) {
                display.println("Enrolled");
            }
        }
        
        display.display();
    }
    http.end();
    delay(5000);
}

void handleFingerprintEnrollment() {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Place finger on sensor");
    display.println("to enroll...");
    display.display();

    Serial.println("Waiting for fingerprint...");
    int fingerprintID = enrollFingerprint();
    
    if (fingerprintID == -2) {  // Special code for duplicate fingerprint
        Serial.println("Duplicate fingerprint detected!");
        sendDuplicateFingerprintResponse();
        return;
    }
    
    if (fingerprintID != -1) {
        Serial.println("Fingerprint enrolled! ID: " + String(fingerprintID));
        sendFingerprintToServer(fingerprintID);
    }
}

void sendDuplicateFingerprintResponse() {
    HTTPClient http;
    http.begin(String(server) + "api/students/" + String(currentStudentId) + "/enroll/");
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["fingerprint_id"] = -2;  // Special code for duplicate
    doc["is_duplicate"] = true;
    doc["existing_id"] = finger.fingerID;  // Add the existing fingerprint ID
    String jsonString;
    serializeJson(doc, jsonString);

    int httpCode = http.POST(jsonString);

    if (httpCode == 200) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Duplicate finger!");
        display.println("Cannot add!");
        display.display();
        Serial.println("Duplicate fingerprint response sent");
        delay(2000);
    }

    http.end();
    isEnrolling = false;
    currentStudentId = -1;
}

int enrollFingerprint() {
    uint8_t id = currentStudentId;  // Use the student ID as fingerprint ID
    uint8_t p = -1;
    bool fingerDetected = false;
    int consecutiveReads = 0;
    
    // Clear any previous data and buffers
    finger.getTemplateCount();
    finger.fingerFastSearch();  // Clear search buffer
    
    // Wait for finger to be placed with confirmation
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Place finger");
    display.println("on sensor...");
    display.display();
    
    // Wait for a stable finger detection
    while (!fingerDetected) {
        p = finger.getImage();
        if (p == FINGERPRINT_OK) {
            consecutiveReads++;
            if (consecutiveReads >= 3) {  // Need 3 consecutive successful reads
                fingerDetected = true;
            }
        } else {
            consecutiveReads = 0;  // Reset counter if read fails
            delay(100);
        }
    }
    
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Got it!");
    display.println("Hold still...");
    display.display();
    delay(1000);  // Give user time to see the message
    
    // Convert and check for duplicate
    p = finger.image2Tz(1);
    if (p != FINGERPRINT_OK) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error!");
        display.println("Try again");
        display.display();
        delay(2000);
        return -1;
    }
    
    // Check for duplicate before proceeding
    p = finger.fingerFastSearch();
    if (p == FINGERPRINT_OK && finger.confidence >= 50) {  // Added confidence threshold
        // Found a match with good confidence
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Fingerprint");
        display.println("already enrolled!");
        display.display();
        delay(2000);
        return -2;  // Special code for duplicate fingerprint
    } else if (p == FINGERPRINT_OK && finger.confidence < 50) {
        // Low confidence match, proceed with enrollment
        Serial.println("Low confidence match, proceeding with enrollment");
    } else if (p == FINGERPRINT_NOTFOUND) {
        // No match found, proceed with enrollment
        Serial.println("No matching fingerprint found");
    } else {
        // Error in search
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error!");
        display.println("Try again");
        display.display();
        delay(2000);
        return -1;
    }
    
    // Get next available ID
    p = finger.getTemplateCount();
    if (p == FINGERPRINT_OK) {
        id = finger.templateCount + 1;
    } else {
        id = 1;
    }
    
    // Remove finger instruction
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Now lift");
    display.println("your finger");
    display.display();
    
    // Wait for finger removal with confirmation
    consecutiveReads = 0;
    while (consecutiveReads < 3) {  // Need 3 consecutive no-finger reads
        p = finger.getImage();
        if (p == FINGERPRINT_NOFINGER) {
            consecutiveReads++;
        } else {
            consecutiveReads = 0;
        }
        delay(100);
    }
    
    delay(1000);  // Extra delay after finger removal
    
    // Second placement instruction
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Place same");
    display.println("finger again");
    display.display();
    
    // Wait for second placement with confirmation
    fingerDetected = false;
    consecutiveReads = 0;
    while (!fingerDetected) {
        p = finger.getImage();
        if (p == FINGERPRINT_OK) {
            consecutiveReads++;
            if (consecutiveReads >= 3) {  // Need 3 consecutive successful reads
                fingerDetected = true;
            }
        } else {
            consecutiveReads = 0;
            delay(100);
        }
    }
    
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Got it!");
    display.println("Processing...");
    display.display();
    
    // Convert second scan
    p = finger.image2Tz(2);
    if (p != FINGERPRINT_OK) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error!");
        display.println("Try again");
        display.display();
        delay(2000);
        return -1;
    }
    
    // Create the model
    p = finger.createModel();
    if (p != FINGERPRINT_OK) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Fingerprints");
        display.println("did not match!");
        display.display();
        delay(2000);
        return -1;
    }
    
    // Store the model
    p = finger.storeModel(id);
    if (p != FINGERPRINT_OK) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error!");
        display.println("Try again");
        display.display();
        delay(2000);
        return -1;
    }
    
    // Success!
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Success!");
    display.println("Finger enrolled");
    display.display();
    delay(2000);
    
    return id;
}

void sendFingerprintToServer(int fingerprintID) {
    HTTPClient http;
    http.begin(String(server) + "api/students/" + String(currentStudentId) + "/enroll/");
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["fingerprint_id"] = fingerprintID;
    String jsonString;
    serializeJson(doc, jsonString);

    int httpCode = http.POST(jsonString);

    if (httpCode == 200) {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Fingerprint enrolled!");
        display.display();
        Serial.println("Fingerprint enrolled successfully!");
        delay(2000);
    } else {
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Enrollment failed!");
        display.display();
        Serial.println("Enrollment failed!");
        delay(2000);
    }

    http.end();
    isEnrolling = false;
    currentStudentId = -1;
}

void startEnrollment(int studentId) {
    currentStudentId = studentId;
    isEnrolling = true;
    Serial.println("Starting enrollment for student ID: " + String(studentId));
}

bool checkSpecialWorkingDay(int& followDay) {
    HTTPClient http;
    http.begin(String(server) + "api/check_special_working_day/");
    int httpCode = http.GET();

    Serial.println("Checking special working day...");
    Serial.print("HTTP Response code: ");
    Serial.println(httpCode);

    if (httpCode == 200) {
        String payload = http.getString();
        Serial.print("Response payload: ");
        Serial.println(payload);
        
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, payload);
        
        if (error) {
            Serial.print("JSON parsing failed: ");
            Serial.println(error.c_str());
            http.end();
            return false;
        }
        
        if (doc["is_special_day"]) {
            followDay = doc["follow_day"].as<int>();
            String description = doc["description"].as<const char*>();
            
            Serial.println("Special working day detected!");
            Serial.print("Following day: ");
            Serial.println(followDay);
            Serial.print("Description: ");
            Serial.println(description);
            
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println("Special Working Day!");
            display.println("----------------");
            display.println(description);
            display.display();
            delay(2000);
            return true;
        } else {
            Serial.println("No special working day today");
        }
    } else {
        Serial.print("HTTP request failed with code: ");
        Serial.println(httpCode);
    }
    http.end();
    return false;
}

void sendAttendancePunch(int fingerprintID) {
    HTTPClient http;
    http.begin(String(server) + "api/punch/");
    http.addHeader("Content-Type", "application/json");

    // Get current time and day
    struct tm timeinfo;
    String subjectCode = "";
    if(getLocalTime(&timeinfo)) {
        int hour = timeinfo.tm_hour;
        int minute = timeinfo.tm_min;
        int dayOfWeek = timeinfo.tm_wday; // 0 = Sunday, 1 = Monday, etc.
        int originalDayOfWeek = dayOfWeek;

        // First check if it's a special working day
        int followDay = -1;
        if (checkSpecialWorkingDay(followDay)) {
            dayOfWeek = followDay; // Use the timetable of the specified day
        }
        // If not a special day, check if it's Sunday or Saturday
        else if (dayOfWeek == 0 || dayOfWeek == 6) {
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println(dayOfWeek == 0 ? "Today is Sunday!" : "Today is Saturday!");
            display.println("No classes today");
            display.display();
            delay(2000);
            return;
        }

        // Regular schedule (using possibly modified dayOfWeek)
        if (hour >= 9 && hour < 10) {
            // Monday & Wednesday
            if ((dayOfWeek == 1 || dayOfWeek == 3) && hour == 9) {
                subjectCode = "BECE-524_KA";  // Control System
            } 
            // Tuesday & Thursday
            else if ((dayOfWeek == 2 || dayOfWeek == 4) && hour == 9) {
                subjectCode = "BECE-525_RL";  // Computer Network
            } 
            // Friday
            else if (dayOfWeek == 5 && hour == 9) {
                subjectCode = "BECE-558_RG";  // Design Lab
            } 
            else {
                subjectCode = "BELE-570_RG";  // Linear Integrated Circuit Analysis
            }
        }
        else if (hour >= 10 && hour < 11) {
            if ((dayOfWeek == 1 || dayOfWeek == 3) && hour == 10) {
                subjectCode = "BECE-555_AB";  // VHDL
            } else if ((dayOfWeek == 2 || dayOfWeek == 4) && hour == 10) {
                subjectCode = "BECE-526_RL";  // Computer Network Lab
            } else if (dayOfWeek == 5 && hour == 10) {
                subjectCode = "BPD-II";  // Professional Development II
            } else {
                subjectCode = "BECE-562_AG";  // Project Lab
            }
        }
        else if (hour >= 11 && hour < 12) {
            if ((dayOfWeek == 1 || dayOfWeek == 3) && hour == 11) {
                subjectCode = "BHUM-005_AS";  // Humanities
            } else if ((dayOfWeek == 2 || dayOfWeek == 4) && hour == 11) {
                subjectCode = "BECE-558_RG";  // Design Lab
            } else if (dayOfWeek == 5 && hour == 11) {
                subjectCode = "BECE-524_KA";  // Control System
            } else {
                subjectCode = "BECE-525_RL";  // Computer Network
            }
        }
        else if (hour >= 12 && hour < 13) {
            subjectCode = "BECE-526_RL";  // Computer Network Lab
        }
        else if (hour >= 14 && hour < 15) {
            subjectCode = "BECE-562_AG";  // Project Lab
        }
        else if (hour >= 15 && hour < 16) {
            subjectCode = "BECE-555_AB";  // VHDL
        }
        else if (hour >= 16 && hour < 16.5) {
            subjectCode = "BHUM-005_AS";  // Humanities
        }
    }

    StaticJsonDocument<200> doc;
    doc["fingerprint_id"] = fingerprintID;
    if(subjectCode.length() > 0) {
        doc["subject_code"] = subjectCode;
    }
    String jsonString;
    serializeJson(doc, jsonString);

    Serial.println("Sending attendance punch with fingerprint ID: " + String(fingerprintID));
    Serial.println("JSON data: " + jsonString);

    int httpCode = http.POST(jsonString);

    if (httpCode == 200) {
        String payload = http.getString();
        Serial.println("Response: " + payload);
        StaticJsonDocument<200> response;
        deserializeJson(response, payload);
        
        if (response["status"] == "success") {
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println("Attendance");
            display.println("Recorded!");
            display.println(response["student_name"].as<const char*>());
            display.println(response["punch_type"].as<const char*>());
            if(response["subject"]) {
                display.println(response["subject"].as<const char*>());
            }
            display.display();
            Serial.println(response["message"].as<const char*>());
            delay(2000);
        } else {
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println("Error!");
            display.println(response["message"].as<const char*>());
            display.display();
            Serial.println(response["message"].as<const char*>());
            delay(2000);
        }
    } else {
        String error = http.getString();
        Serial.println("HTTP Error: " + String(httpCode));
        Serial.println("Error response: " + error);
        
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Error!");
        display.println("Failed to record");
        display.display();
        Serial.println("Failed to record attendance");
        delay(2000);
    }

    http.end();
}