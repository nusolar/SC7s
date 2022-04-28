import React, { Component } from 'react'

export default class Summary extends Component {
    render() {
        return (
            <div >
                <h2>Questions</h2>
                <form>
            <label>What do you do?</label>
            <div id='block-1'>
                <label for='option-1'>
                  <input type='radio' name='option' value='1' id='option-1'/>
                  College</label>
                <span id='result-1'></span>
              </div>
    
            
              <div id='block-2'>
                <label for='option-2'>
                  <input type='radio' name='option' value='2' id='option-2'/>
                  High School</label>
                <span id='result-2'></span>
              </div>
   
            
              <div id='block-3'>
                <label for='option-3'>
                  <input type='radio' name='option' value='3' id='option-13'/>
                  Work</label>
                <span id='result-3'></span>
              </div>
          
            
              <div id='block-4'>
                <label for='option-4'>
                  <input type='radio' name='option' value='4' id='option-4'/>
                  Nothing</label>
                <span id='result-4'></span>
              </div>

              <button type="button" >Submit</button>
        </form>

                
            </div>
        )
    }
}
