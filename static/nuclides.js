window.addEventListener( 'load', function () {
	$( '#nuclides' ).panzoom( {
		$zoomIn: $( '#nuclides-zoom-in' ),
		$zoomOut: $( '#nuclides-zoom-out' ),
		$zoomRange: $( '#nuclides-zoom-range' ),
		$reset: $( '#nuclides-reset' )
	} );
} );
