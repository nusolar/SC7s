import React, { Component } from 'react'

export default class Header extends Component {
    render() {
        return (
            <div class="container">
                <div class="row">
                    <div class="col">
                        <div class="card ">
                            <div class="card-body">
                                <h5 class="card-title">Main Current</h5>
                                <h1 class="card-text">22.22 </h1>

                            </div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="card ">
                            <div class="card-body">
                                <h5 class="card-title">MPPT1</h5>
                                <h1 class="card-text">88.88 </h1>

                            </div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="card ">
                            <div class="card-body">
                                <h5 class="card-title">MPPT2</h5>
                                <h1 class="card-text">99.99 </h1>

                            </div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="card ">
                            <div class="card-body">
                                <h5 class="card-title">RPM</h5>
                                <h1 class="card-text">33.33</h1>

                            </div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="card ">
                            <div class="card-body">
                                <h6 class="card-title">Lowest Voltage</h6>
                                <h1 class="card-text">66.66</h1>

                            </div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="card ">
                            <div class="card-body">
                                <h5 class="card-title">Highest Temp</h5>
                                <h1 class="card-text">77.66</h1>

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
}
