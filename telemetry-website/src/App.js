import './App.css';

import 'bootstrap/dist/css/bootstrap.min.css'

import Header from './Components/Header';
import Summary from './Components/Summary';
import Gps from './Components/gps';
import Batteries from './Components/Batteries';
import Temperatures from './Components/Temperatures';
import Menu from './Components/menu'
import React, { useState } from 'react';


function curr_display(component_name) {
    switch (component_name) {
      case "Summary":
        return <Summary />
      case "Gps":
        return <Gps />
      case "Batteries":
        return <Batteries />
      case "Temperatures":
        return <Temperatures />
      default:
        return <Summary />
  }
}

// function radio_data() {
//   var SerialPort = require('serialport').SerialPort;
//   var xbee_api = require('xbee-api');
//   var C = xbee_api.constants;
  
//   var xbeeAPI = new xbee_api.XBeeAPI({
//     api_mode: 1
//   });
  
//   var serialport = new SerialPort("COM5", {
//     baudrate: 57600,
//   });
  
//   serialport.pipe(xbeeAPI.parser);
//   xbeeAPI.builder.pipe(serialport);
  
  // serialport.on("open", function() {
  //   var frame_obj = { // AT Request to be sent
  //     type: C.FRAME_TYPE.AT_COMMAND,
  //     command: "NI",
  //     commandParameter: [],
  //   };
  
  //   xbeeAPI.builder.write(frame_obj);
  // });
  
  // All frames parsed by the XBee will be emitted here
//   xbeeAPI.parser.on("data", function(frame) {
//       console.log(">>", frame);
//   });
//}

class App extends React.Component{
  constructor(props){
    super(props)

    this.handleToUpdate = this.handleToUpdate.bind(this);

    this.state = {
      curr_display: "Summary",
      value: new Date()
    }
    
  }

  //test = setInterval( radio_data, 100);

  handleToUpdate(click_state){
    this.setState({curr_display:click_state})
  }

  
  render() {
    
    
  return (
    <div className="App">
      <div className="container">

        <Header />

        <br/>
        <br/>
        <div className="container">
          <div class="row">

          <div className="col-3">
            <Menu action={this.handleToUpdate} time_value={this.value}/>
          </div>
          
          <div class="col">
            {curr_display(this.state.curr_display)}
          </div>
          
          </div>
        </div>
      </div>

    </div>
  );
  }
}

export default App;
