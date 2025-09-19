if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.clientside = {
    get_location: function(n) {
        if (!n) {
            return window.dash_clientside.no_update;
        }
        if (!navigator.geolocation) {
            return {error: "unsupported"};
        }
        return new Promise(function(resolve) {
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    resolve({
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        accuracy_m: pos.coords.accuracy,
                        ts: pos.timestamp
                    });
                },
                function(err) {
                    resolve({error: err.code, message: err.message});
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        });
    }
};
