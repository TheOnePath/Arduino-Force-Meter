const float a_reading = 22.0;
const float a_load = 0.98;
const float b_reading = 57.0;
const float b_load = 4.9;

unsigned long time;
int interval = 1;

void setup() {
  Serial.begin(9600);
}

void loop() {
  main_loop();
}

void main_loop(){
  float new_measure = analogRead(0);
  float load = ((b_load - a_load) / (b_reading - a_reading)) * (new_measure - a_reading) + a_load;
  
  //if (load > 0.43){
    //Serial.print(load);
    //Serial.print("\n");
    if (millis() > time + interval){
      Serial.print("Reading: ");
      Serial.print(new_measure, 1);
      Serial.print(" ");
      Serial.print(load, 2);
      Serial.print(" ");
      time = millis();
      Serial.print(" ");
      Serial.print(time);
      Serial.print("\n");
    } 
 // }
}
