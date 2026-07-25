'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
@－－－－湖南创乐博智能科技有限公司－－－－
@  文件名：LOBOROBOT.py 
@  版本：V2.0 
@  author: zhulin
@  说明：机器人控制库
 驱动机器人的基本运动库函数
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
import time
import math
import smbus
from gpiozero import Motor


# 控制机器人库
class LOBOROBOT():
    def __init__(self):
        self.motor1 = Motor(24, 25)  #  机器人Motor1
        self.motor2 = Motor(27, 26)  #  机器人Motor2
        self.motor3 = Motor(5, 6)    #  机器人Motor3
        self.motor4 = Motor(22, 9)   #  机器人Motor4

    # 前进
    def t_up(self,speed,t_time):
        self.motor1.forward(speed)
        self.motor2.forward(speed)
        self.motor3.forward(speed)
        self.motor4.forward(speed)
        time.sleep(t_time)
        
    #后退
    def t_down(self,speed,t_time):
        self.motor1.backward(speed)
        self.motor2.backward(speed)
        self.motor3.backward(speed)
        self.motor4.backward(speed)
        time.sleep(t_time)
        
    # 左移
    def moveLeft(self,speed,t_time):
        self.motor1.backward(speed)
        self.motor2.forward(speed)
        self.motor3.forward(speed)
        self.motor4.backward(speed)
        time.sleep(t_time)

    #右移
    def moveRight(self,speed,t_time):
        self.motor1.forward(speed)
        self.motor2.backward(speed)
        self.motor3.backward(speed)
        self.motor4.forward(speed)
        time.sleep(t_time)
        
    # 左转
    def turnLeft(self,speed,t_time):
        self.motor1.backward(speed)
        self.motor2.forward(speed)
        self.motor3.backward(speed)
        self.motor4.forward(speed)
        time.sleep(t_time)
    
    # 右转
    def turnRight(self,speed,t_time):
        self.motor1.forward(speed)
        self.motor2.backward(speed)
        self.motor3.forward(speed)
        self.motor4.backward(speed)
        time.sleep(t_time)
    
    # 前左斜
    def forward_Left(self,speed,t_time):
        self.motor1.stop()
        self.motor2.forward(speed)
        self.motor3.forward(speed)
        self.motor4.stop()
        time.sleep(t_time)

    # 前右斜
    def forward_Right(self,speed,t_time):
        self.motor1.forward(speed)
        self.motor2.stop()
        self.motor3.stop()
        self.motor4.forward(speed)
        time.sleep(t_time)

    # 后左斜
    def backward_Left(self,speed,t_time):
        self.motor1.backward(speed)
        self.motor2.stop()
        self.motor3.stop()
        self.motor4.backward(speed)
        time.sleep(t_time)
    
    # 后右斜
    def backward_Right(self,speed,t_time):
        self.motor1.stop()
        self.motor2.backward(speed)
        self.motor3.backward(speed)
        self.motor4.stop()
        time.sleep(t_time)

    # 停止
    def t_stop(self,t_time):
        self.motor1.stop()
        self.motor2.stop()
        self.motor3.stop()
        self.motor4.stop()
        time.sleep(t_time)

        # 辅助功能，使设置舵机脉冲宽度更简单。
    def set_servo_pulse(self,channel,pulse):
        pulse_length = 1000000    # 1,000,000 us per second
        pulse_length //= 60       # 60 Hz
        print('{0}us per period'.format(pulse_length))
        pulse_length //= 4096     # 12 bits of resolution
        print('{0}us per bit'.format(pulse_length))
        pulse *= 1000
        pulse //= pulse_length
        self.pwm.setPWM(channel, 0, pulse)

    # 设置舵机角度函数  
    def set_servo_angle(self,channel,angle):
        angle=4096*((angle*11)+500)/20000
        self.pwm.setPWM(channel,0,int(angle))


