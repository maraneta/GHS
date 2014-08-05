var FORMULA_EDIT = {};

FORMULA_EDIT.refresh_delete_buttons = function() {
    jQuery(".deleterow").on("click", function(){
        var $killrow = $(this).parent('tr');
            $killrow.addClass("danger");

        var row = $(this).parent('tr')[0];
        var i = row.rowIndex;

        $killrow.fadeOut(1000, function(){
            $(this).remove();
            var form_id = $('#id_form-TOTAL_FORMS').val();
            jQuery('#id_form-TOTAL_FORMS').val(Number(form_id)-1);
            var value_to_decrement = i;
            jQuery('#formula-rows tr').each(
                function(index, value){
                    if (i - 1 < index ) {
                        6
                        jQuery(value).find('input[type="text"]').each(
                            function( input_index, input_value) {
                                var my_name = jQuery(input_value).attr('name');
                                var new_name = my_name.replace(value_to_decrement, value_to_decrement-1);
                                jQuery(input_value).attr('name', new_name);
                                var my_id = jQuery(input_value).attr('id');
                                var new_id = my_id.replace(value_to_decrement, value_to_decrement-1)
                                jQuery(input_value).attr('id', new_id);

                        });
                        value_to_decrement += 1;
                    }
            });

    });});
};

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

    FORMULA_EDIT.refresh_delete_buttons();

    jQuery(".addnewrow").click(function() {

		var form_id = $('#id_form-TOTAL_FORMS').val();
		jQuery('#id_form-TOTAL_FORMS').val(Number(form_id)+1);

        jQuery('#formula-rows tr:last').after(
                '<tr class="formula_row">' +
                '<td class="number-cell"><input type="text" name="form-' + form_id + '-cas" id="id_form-' + form_id + '-cas" /></td>' +
                '<td class="amount-cell"><input type="text" name="form-' + form_id + '-amount" id="id_form-' + form_id + '-amount" /></td>' +
                '<td class="deleterow">' +
                '<div class="glyphicon glyphicon-remove"></div></td>' +
                '</tr>');
        jQuery('#id_form-' + form_id + '-cas').focus();

        FORMULA_EDIT.refresh_delete_buttons();

        return false;


    })

});
