import React from 'react';

function DataCard({name, value}) {
    return (
        <div class="card ">
            <div class="card-body">
                <h5 class="card-title">{name}</h5>
                <h1 class="card-text">{value}</h1>
            </div>
        </div>
    )
}

export default DataCard