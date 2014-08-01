var FORMULA_EDIT = {};

jQuery(document).ready(function(){  
    

    jQuery('#formula-rows').delegate('.number-cell input', 'keyup', function(e) {
        var $this = $(this);
        var row = $this.closest("tr");
        
        $this.autocomplete({
            source: '/ghs_app/ingredient_autocomplete',
            minLength: 1,
            position: {my: 'left top', at: 'right top'},
            select: function( event, ui ) {
                // ui.item.value is the item of interest
                row.find('.number-cell input').val( ui.item.value );
                // FORMULA_EDIT.get_name_from_cas(row);
            }
        });
    });
    
});