#include <iostream>
#include <string>

class Motor {
private:
    std::string brand;
    int speedBPM;
    std::string operativeMode;
    int age;

public:
    /*Constructor con lista de inicializacion(la forma correcta)*/
    Motor(const std::string& b, int s, const std::string& mode, int a)
       : brand(b), speedBPM(s), operativeMode(mode), age(a)
       {
       }
       /*Getter: encapsulacion en accion*/
       int spped() const { return speedBPM; }

       void printStatus() const
       {
       std::cout <<"The motor is currently on " << operativeMode
                 <<", at a speed of " << speedBPM << " BPM. "
                 << " This model is from the " << brand
                 << " company (" << age << "years old).\n";

  }
};

/*Herencia: ServoMotor ES UN Motor*/
class ServoMotor : public Motor { 
private:
   int pointA = 40;
   int pointB = 60;
   int pointC = 90;

public: 
    ServoMotor(const std::string& b, int s, const std::string& mode, int a,
               int pa, int pb, int pc)
        : Motor(b, s, mode, a), /*Primero se construye la base*/
        pointA(pa), pointB(pb), pointC(pc)
        {
        }

        void printAngles() const
        {
            std::cout <<"Servo points: " << pointA << " / " << pointB
            << "/"  << pointC << " \n";
        }
};
int main()
{
    Motor m("Siemens", 1200, "automatic", 3);
    m.printStatus();

    ServoMotor s("Festo", 800, "manual", 1, 40, 60, 90);
    s.printStatus();      /*metodo heredado del motor*/
    s.printAngles();      /*metodo propio */
    
    return 0;
}
