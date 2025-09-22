<template>
    <div>
        <FormComponent/>
        <ListData :employees="employees" />
    </div>
</template>


<script>
import FormComponent from "./components/FormComponent.vue"
import ListData from "./components/ListData.vue"
export default {
    name: "App",
    components:{
        ListData,
        FormComponent
    },
    data(){
        return{
            employees:[
                {name:"นาส",salary:55555},
                {name:"อาส",salary:1205},
                {name:56,salary:"lol"} 
            ]
        }
    }
}
</script>


<style>

</style>