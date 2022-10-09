import React, { Component } from 'react'
import DataCard from './DataCard'

export default class Header extends Component {
    render() {
        return (
            <div class="container">
                <div class="row">
                    <div class="col">
                        <DataCard name="Main Current" value="22.22" />
                    </div>
                    <div class="col">
                        <DataCard name="MPPT1" value="88.88" />
                    </div>
                    <div class="col">
                        <DataCard name="MPPT2" value="99.99" />
                    </div>
                    <div class="col">
                        <DataCard name="RPM" value="33.33" />
                    </div>
                    <div class="col">
                        <DataCard name="Lowest Voltage" value="66.66" />
                    </div>
                    <div class="col">
                        <DataCard name="Highest Temp" value="77.66" />
                    </div>
                </div>
            </div>
        )
    }
}
