#include <dht.h>
dht DHT;
#define DHT11_PIN 7

void setup() {
  Serial.begin(115200);

}

void loop() {
  int chk = DHT.read11(DHT11_PIN);
  Serial.println("start");
  Serial.println(String(DHT.temperature));
  Serial.println(String(DHT.humidity));
  delay(500);


}
