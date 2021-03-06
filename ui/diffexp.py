<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>400</width>
    <height>300</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Dialog</string>
  </property>
  <widget class="QDialogButtonBox" name="buttonBox">
   <property name="geometry">
    <rect>
     <x>50</x>
     <y>260</y>
     <width>341</width>
     <height>32</height>
    </rect>
   </property>
   <property name="orientation">
    <enum>Qt::Horizontal</enum>
   </property>
   <property name="standardButtons">
    <set>QDialogButtonBox::Cancel|QDialogButtonBox::Ok</set>
   </property>
  </widget>
  <widget class="QLabel" name="lFSExpSamples_2">
   <property name="geometry">
    <rect>
     <x>60</x>
     <y>90</y>
     <width>59</width>
     <height>16</height>
    </rect>
   </property>
   <property name="text">
    <string>Value1:</string>
   </property>
  </widget>
  <widget class="QComboBox" name="cField">
   <property name="geometry">
    <rect>
     <x>110</x>
     <y>50</y>
     <width>191</width>
     <height>26</height>
    </rect>
   </property>
  </widget>
  <widget class="QLineEdit" name="tValue1">
   <property name="geometry">
    <rect>
     <x>110</x>
     <y>90</y>
     <width>191</width>
     <height>21</height>
    </rect>
   </property>
  </widget>
  <widget class="QLabel" name="lFSExpSamples_3">
   <property name="geometry">
    <rect>
     <x>50</x>
     <y>230</y>
     <width>71</width>
     <height>16</height>
    </rect>
   </property>
   <property name="text">
    <string>New name:</string>
   </property>
  </widget>
  <widget class="QCheckBox" name="cAll">
   <property name="geometry">
    <rect>
     <x>310</x>
     <y>130</y>
     <width>89</width>
     <height>20</height>
    </rect>
   </property>
   <property name="text">
    <string>All</string>
   </property>
  </widget>
  <widget class="QLineEdit" name="tNewName">
   <property name="geometry">
    <rect>
     <x>120</x>
     <y>230</y>
     <width>161</width>
     <height>21</height>
    </rect>
   </property>
  </widget>
  <widget class="QPushButton" name="bFieldValues1">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>80</y>
     <width>61</width>
     <height>32</height>
    </rect>
   </property>
   <property name="text">
    <string>Values</string>
   </property>
  </widget>
  <widget class="QLabel" name="lFSExpName">
   <property name="geometry">
    <rect>
     <x>190</x>
     <y>10</y>
     <width>59</width>
     <height>16</height>
    </rect>
   </property>
   <property name="text">
    <string>ExpName</string>
   </property>
  </widget>
  <widget class="QLabel" name="label">
   <property name="geometry">
    <rect>
     <x>70</x>
     <y>50</y>
     <width>41</width>
     <height>16</height>
    </rect>
   </property>
   <property name="text">
    <string>Field:</string>
   </property>
  </widget>
  <widget class="QPushButton" name="bFieldValues2">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>120</y>
     <width>61</width>
     <height>32</height>
    </rect>
   </property>
   <property name="text">
    <string>Values</string>
   </property>
  </widget>
  <widget class="QLineEdit" name="tValue2">
   <property name="geometry">
    <rect>
     <x>110</x>
     <y>130</y>
     <width>191</width>
     <height>21</height>
    </rect>
   </property>
  </widget>
  <widget class="QLabel" name="lFSExpSamples_4">
   <property name="geometry">
    <rect>
     <x>60</x>
     <y>130</y>
     <width>59</width>
     <height>16</height>
    </rect>
   </property>
   <property name="text">
    <string>Value2:</string>
   </property>
  </widget>
  <widget class="QComboBox" name="cMethod">
   <property name="geometry">
    <rect>
     <x>120</x>
     <y>170</y>
     <width>104</width>
     <height>26</height>
    </rect>
   </property>
   <item>
    <property name="text">
     <string>all</string>
    </property>
   </item>
   <item>
    <property name="text">
     <string>ranksum</string>
    </property>
   </item>
   <item>
    <property name="text">
     <string>binary</string>
    </property>
   </item>
   <item>
    <property name="text">
     <string>mean</string>
    </property>
   </item>
   <item>
    <property name="text">
     <string>freqpres</string>
    </property>
   </item>
  </widget>
  <widget class="QLabel" name="label_2">
   <property name="geometry">
    <rect>
     <x>60</x>
     <y>170</y>
     <width>51</width>
     <height>20</height>
    </rect>
   </property>
   <property name="text">
    <string>Method:</string>
   </property>
  </widget>
  <widget class="QLabel" name="lFSExpSamples_5">
   <property name="geometry">
    <rect>
     <x>300</x>
     <y>170</y>
     <width>31</width>
     <height>16</height>
    </rect>
   </property>
   <property name="text">
    <string>FDR:</string>
   </property>
  </widget>
  <widget class="QDoubleSpinBox" name="sFDR">
   <property name="geometry">
    <rect>
     <x>330</x>
     <y>170</y>
     <width>67</width>
     <height>24</height>
    </rect>
   </property>
   <property name="maximum">
    <double>1.000000000000000</double>
   </property>
   <property name="singleStep">
    <double>0.050000000000000</double>
   </property>
   <property name="value">
    <double>0.100000000000000</double>
   </property>
  </widget>
 </widget>
 <resources/>
 <connections>
  <connection>
   <sender>buttonBox</sender>
   <signal>accepted()</signal>
   <receiver>Dialog</receiver>
   <slot>accept()</slot>
   <hints>
    <hint type="sourcelabel">
     <x>248</x>
     <y>254</y>
    </hint>
    <hint type="destinationlabel">
     <x>157</x>
     <y>274</y>
    </hint>
   </hints>
  </connection>
  <connection>
   <sender>buttonBox</sender>
   <signal>rejected()</signal>
   <receiver>Dialog</receiver>
   <slot>reject()</slot>
   <hints>
    <hint type="sourcelabel">
     <x>316</x>
     <y>260</y>
    </hint>
    <hint type="destinationlabel">
     <x>286</x>
     <y>274</y>
    </hint>
   </hints>
  </connection>
 </connections>
</ui>
