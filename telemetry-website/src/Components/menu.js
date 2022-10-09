import React, { Component } from 'react'

export default class menu extends Component {
    

    render() {
        var handleToUpdate = this.props.action;
        

        return (
            <div>
            <div class="col">
              <div class="card_holder" onClick={() => handleToUpdate("Summary")}>
                <div class="card-body">
                  <h5 class="card-title text-white">Summary</h5>
                </div>
              </div>
              
              <div class="card"  onClick={() => handleToUpdate("Gps")}>
                <div class="card-body">
                  <h5 class="card-title text_white">GPS</h5>
                </div>
              </div>
              
              <div class="card "  onClick={() => handleToUpdate("Batteries")}>
                <div class="card-body">
                  <h5 class="card-title">Batteries</h5>
                </div>
              </div>
              
              <div class="card "  onClick={() => handleToUpdate("Temperatures")}>
                <div class="card-body">
                  <h5 class="card-title">Temperatures</h5>
                </div>
              </div> 

              <div class="card ">
                <div class="card-body">
                  <p class="card-title">Time:  </p>
                </div>
              </div> 
            </div>


                
            </div>
        )
    }
}
